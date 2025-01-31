module.exports = {
  presets: [
    "@babel/preset-env",
    "@babel/preset-react"
  ],
  plugins: [
    "@babel/plugin-proposal-optional-chaining",
    "@babel/plugin-proposal-nullish-coalescing-operator",
    "@babel/plugin-transform-runtime"
  ],
  ignore: [
    function(filepath) {
      return !filepath.includes("node_modules/mqtt");
    }
  ]
};
