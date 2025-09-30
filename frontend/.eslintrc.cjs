module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  extends: ["eslint:recommended", "plugin:svelte/recommended", "prettier"],
  plugins: ["svelte"],
  env: {
    browser: true,
    es2021: true,
  },
  overrides: [
    {
      files: ["*.svelte"],
      parser: "svelte-eslint-parser",
    },
  ],
};
