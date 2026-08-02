module.exports = {
  extends: ["expo", "plugin:@typescript-eslint/recommended"],
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint"],
  rules: {
    "import/namespace": "off",
    "import/no-unresolved": "off",
    "react/no-unescaped-entities": "off"
  }
};
