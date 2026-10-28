"use strict";

const fs = require("node:fs");

// Called by actions/github-script only after all validation jobs pass.
// Published releases are immutable. Upload everything to a draft first.
module.exports = async function publish({github, context, core}, read = fs.readFileSync) {
  const {version} = JSON.parse(read("custom_components/room_comfort/manifest.json", "utf8"));
  if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error("A stable manifest version is required");
  const tag = `v${version}`, repo = context.repo;
  let release;
  try {
    release = (await github.rest.repos.getReleaseByTag({...repo, tag})).data;
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  if (release && !release.draft) {
    core.notice(`${tag} is already published. Bump the manifest version for the next release.`);
    return;
  }
  if (release && release.target_commitish !== context.sha) {
    throw new Error(`Draft ${tag} belongs to another commit; inspect it before retrying.`);
  }
  try {
    const existing = (await github.rest.git.getRef({...repo, ref: `tags/${tag}`})).data;
    if (existing.object.sha !== context.sha) throw new Error(`Tag ${tag} points elsewhere and will not be moved.`);
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  const body = read("dist/release-notes.md", "utf8");
  // Check both ZIP files before making any GitHub mutation.
  const files = ["install", "source"].map(kind => {
    const name = `room-comfort-${version}-${kind}.zip`;
    return {name, data: read(`dist/${name}`)};
  });
  if (!release) {
    release = (await github.rest.repos.createRelease({
      ...repo, tag_name: tag, target_commitish: context.sha,
      name: `Room Comfort ${version}`, body, draft: true, prerelease: false,
    })).data;
  }
  const assets = await github.paginate(github.rest.repos.listReleaseAssets, {...repo, release_id: release.id});
  for (const {name, data} of files) {
    const previous = assets.find(asset => asset.name === name);
    if (previous) await github.rest.repos.deleteReleaseAsset({...repo, asset_id: previous.id});
    await github.rest.repos.uploadReleaseAsset({
      ...repo, release_id: release.id, name, data,
      headers: {"content-type": "application/zip", "content-length": data.length},
    });
  }
  const result = await github.rest.repos.updateRelease({
    ...repo, release_id: release.id, body, draft: false, prerelease: false, make_latest: "true",
  });
  core.notice(`Published ${result.data.html_url}`);
  await core.summary.addHeading(`Released ${tag}`).addLink("Open GitHub release", result.data.html_url).write();
};
