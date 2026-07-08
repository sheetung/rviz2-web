module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    '@vue/eslint-config-prettier'
  ],
  ignorePatterns: [
    'dist/',
    'node_modules/'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  globals: {
    ElMessage: 'readonly'
  },
  rules: {
    'no-case-declarations': 'off',
    'no-console': 'off',
    'no-undef': 'off',
    'no-useless-escape': 'off',
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    'prettier/prettier': 'off',
    'vue/attributes-order': 'off',
    'vue/first-attribute-linebreak': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'off',
    'vue/no-reserved-component-names': 'off',
    'vue/no-unused-components': 'off',
    'vue/no-unused-vars': 'warn',
    'vue/order-in-components': 'off',
    'vue/require-explicit-emits': 'off'
  }
}
