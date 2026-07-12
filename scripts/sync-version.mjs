import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'


const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const versionPath = resolve(root, 'VERSION')
const requestedVersion = process.argv.find(arg => /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(arg))
const checkOnly = process.argv.includes('--check')
const version = requestedVersion || readFileSync(versionPath, 'utf8').trim()

if (!/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(version)) {
  throw new Error(`Invalid semantic version: ${version}`)
}

const jsonFiles = [
  resolve(root, 'frontend/package.json'),
  resolve(root, 'frontend/package-lock.json')
]
const pyprojectPath = resolve(root, 'backend/pyproject.toml')
const uvLockPath = resolve(root, 'backend/uv.lock')
const readmePath = resolve(root, 'README.md')
const readmeEnPath = resolve(root, 'README_en.md')
const projectStatusPath = resolve(root, 'PROJECT_STATUS.md')

const mismatches = []
for (const path of jsonFiles) {
  const document = JSON.parse(readFileSync(path, 'utf8'))
  if (document.version !== version) mismatches.push(path)
  if (path.endsWith('package-lock.json') && document.packages?.['']?.version !== version) {
    mismatches.push(`${path} packages[""]`)
  }
  if (!checkOnly) {
    document.version = version
    if (path.endsWith('package-lock.json') && document.packages?.['']) {
      document.packages[''].version = version
    }
    writeFileSync(path, `${JSON.stringify(document, null, 2)}\n`)
  }
}

const pyproject = readFileSync(pyprojectPath, 'utf8')
const currentPythonVersion = pyproject.match(/^version = "([^"]+)"/m)?.[1]
if (currentPythonVersion !== version) mismatches.push(pyprojectPath)
if (!checkOnly) {
  writeFileSync(pyprojectPath, pyproject.replace(/^version = "[^"]+"/m, `version = "${version}"`))
  writeFileSync(versionPath, `${version}\n`)
}

const textFiles = [
  {
    path: uvLockPath,
    pattern: /(name = "rviz-web-backend"\r?\nversion = ")[^"]+("\r?\n)/,
    replacement: `$1${version}$2`
  },
  {
    path: readmePath,
    pattern: /(当前正式版本：`v)[^`]+(`)/,
    replacement: `$1${version}$2`
  },
  {
    path: readmeEnPath,
    pattern: /(Current release: `v)[^`]+(`)/,
    replacement: `$1${version}$2`
  },
  {
    path: projectStatusPath,
    pattern: /(工程版本：`v)[^`]+(`)/,
    replacement: `$1${version}$2`
  }
]

for (const { path, pattern, replacement } of textFiles) {
  const content = readFileSync(path, 'utf8')
  const current = content.match(pattern)?.[0]
  const updated = content.replace(pattern, replacement)
  if (!current || !current.includes(version)) mismatches.push(path)
  if (!checkOnly) writeFileSync(path, updated)
}

if (checkOnly && mismatches.length > 0) {
  throw new Error(`Version ${version} is not synchronized:\n${mismatches.join('\n')}`)
}

console.log(`${checkOnly ? 'Verified' : 'Synchronized'} RVizWeb ${version}`)
