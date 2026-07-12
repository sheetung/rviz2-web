import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const changelogPath = resolve(root, 'CHANGELOG.md')
const version = process.argv[2]
const note = process.argv[3] || '维护版本发布。'

if (!/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(version || '')) {
  throw new Error('Usage: node scripts/add-release-notes.mjs <version> [note]')
}

const changelog = readFileSync(changelogPath, 'utf8')
if (new RegExp(`^## \\[${version.replaceAll('.', '\\.') }\\]`, 'm').test(changelog)) {
  throw new Error(`CHANGELOG.md already contains ${version}`)
}

const date = new Date().toISOString().slice(0, 10)
const section = `## [${version}] - ${date}\n\n### Changed\n\n- ${note}\n\n`
const firstRelease = changelog.search(/^## \[/m)
const updated = firstRelease === -1
  ? `${changelog.trimEnd()}\n\n${section}`
  : `${changelog.slice(0, firstRelease)}${section}${changelog.slice(firstRelease)}`

writeFileSync(changelogPath, updated)
console.log(`Added CHANGELOG.md entry for ${version}`)
