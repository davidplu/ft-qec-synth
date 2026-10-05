// Optional figure rendering with a caller-supplied Sharp installation.
// Runtime synthesis and report SVG generation have no dependency on Sharp.
const path = require('node:path');
const sharp = require(path.join(process.argv[2], 'sharp'));
const root = path.resolve(__dirname, '../results/v0.4');
(async () => {
  for (const stem of ['trajectories', 'distance_tier_trajectories']) {
    await sharp(path.join(root, stem + '.svg'), { density: 144 })
      .png().toFile(path.join(root, stem + '.png'));
  }
  process.stdout.write('Two scientific figures rendered.\n');
})();
