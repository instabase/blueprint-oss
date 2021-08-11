const webpack = require('webpack');
const path = require('path');
const TsconfigPathsPlugin = require('tsconfig-paths-webpack-plugin');

module.exports = {
  entry: {
    main: './src/main.tsx',
  },
  devtool: 'source-map',
  mode: 'development',
  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        options: {
          sourceMaps: true,
          plugins: [
            '@babel/plugin-transform-runtime',
          ],
          presets: [
            '@babel/preset-env',
            '@babel/preset-react',
            '@babel/preset-typescript',
          ],
        },
      },
      {
        test: /.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    extensions: [
      '.js',
      '.jsx',
      '.ts',
      '.tsx',
    ],
    plugins: [
      new TsconfigPathsPlugin({}),
    ],
  },
  optimization: {
    minimize: false,
  },
  output: {
    path: path.resolve(__dirname, 'dist/'),
    publicPath: './',
    filename: 'bundle.js',
  },
  devServer: {
    contentBase: path.join(__dirname, 'static/'),
    port: 3000,
    publicPath: 'http://localhost:3000/',
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin(),
  ],
};
