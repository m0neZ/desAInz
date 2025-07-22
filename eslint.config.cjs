const { FlatCompat } = require('@eslint/eslintrc');
const js = require('@eslint/js');
const eslintrc = require('./.eslintrc.js');

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
});

module.exports = [
  ...compat.config(eslintrc),
  {
    rules: {
      'no-console': 'error',
      'no-var': 'error',
    },
  },
  { ignores: ['flow-typed/**', 'load_tests/**'] },
];
