module.exports = {
  'rootDir': 'src',
  'transform': {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  "moduleNameMapper": {
    "studio/(.*)": ["<rootDir>/$1"],
  }
}
