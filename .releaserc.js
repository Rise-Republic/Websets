module.exports = {
  branches: [
    'main',
    {
      name: 'beta',
      prerelease: true
    },
    {
      name: 'alpha',
      prerelease: true
    }
  ],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    [
      '@semantic-release/changelog',
      {
        changelogFile: 'CHANGELOG.md',
        changelogTitle: '# Changelog\n\nAll notable changes to this project will be documented in this file.'
      }
    ],
    [
      '@semantic-release/exec',
      {
        prepareCmd: 'echo "Preparing release ${nextRelease.version}"',
        publishCmd: 'echo "Publishing release ${nextRelease.version}"'
      }
    ],
    [
      '@semantic-release/github',
      {
        assets: [
          {
            path: 'artifacts/*.tar.gz',
            label: 'Deployment Package'
          },
          {
            path: 'artifacts/deployment-manifest.json',
            label: 'Deployment Manifest'
          }
        ],
        discussionCategoryName: 'Releases'
      }
    ],
    [
      '@semantic-release/git',
      {
        assets: ['CHANGELOG.md', 'package.json', 'package-lock.json'],
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
      }
    ]
  ],
  preset: 'conventionalcommits',
  releaseRules: [
    { type: 'feat', release: 'minor' },
    { type: 'fix', release: 'patch' },
    { type: 'perf', release: 'patch' },
    { type: 'revert', release: 'patch' },
    { type: 'docs', release: false },
    { type: 'style', release: false },
    { type: 'chore', release: false },
    { type: 'refactor', release: 'patch' },
    { type: 'test', release: false },
    { type: 'build', release: false },
    { type: 'ci', release: false },
    { breaking: true, release: 'major' }
  ],
  parserOpts: {
    noteKeywords: ['BREAKING CHANGE', 'BREAKING CHANGES', 'BREAKING']
  },
  writerOpts: {
    commitsSort: ['subject', 'scope']
  }
};
