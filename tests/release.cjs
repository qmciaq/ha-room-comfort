const {test}=require('node:test');
const assert=require('node:assert/strict');
const publish=require('../scripts/publish_release.cjs');

function fixture({existing,tagSha,failUpload=false,missingZip=false}={}){
  const calls=[];
  const missing=()=>{throw Object.assign(new Error('Not found'),{status:404});};
  const context={repo:{owner:'example',repo:'room-comfort'},sha:'a'.repeat(40)};
  const repos={
    getReleaseByTag:async()=>existing?{data:existing}:missing(),
    createRelease:async data=>{calls.push(['create',data]);return {data:{id:1,target_commitish:context.sha,draft:true}};},
    listReleaseAssets:()=>{},
    deleteReleaseAsset:async data=>calls.push(['delete',data]),
    uploadReleaseAsset:async data=>{calls.push(['upload',data]);if(failUpload&&data.name.endsWith('source.zip'))throw Error('Upload failed');},
    updateRelease:async data=>{calls.push(['publish',data]);return {data:{html_url:'https://example.test/release'}};},
  };
  const github={rest:{repos,git:{getRef:async()=>tagSha?{data:{object:{sha:tagSha}}}:missing()}},paginate:async()=>[]};
  const summary={addHeading(){return this;},addLink(){return this;},async write(){}};
  const core={notice(){},summary};
  const read=(path,encoding)=>{
    if(path.endsWith('manifest.json'))return JSON.stringify({version:'0.5.0'});
    if(missingZip&&path.endsWith('source.zip'))throw Error('Missing ZIP');
    return encoding?'Release notes':Buffer.from('example ZIP');
  };
  return {calls,context,run:()=>publish({github,context,core},read)};
}

test('release stays a draft until both assets are uploaded to the tested commit',async()=>{
  const f=fixture();await f.run();
  assert.deepEqual(f.calls.map(c=>c[0]),['create','upload','upload','publish']);
  assert.equal(f.calls[0][1].target_commitish,f.context.sha);
  assert.equal(f.calls[0][1].tag_name,'v0.5.0');
  assert.equal(f.calls[0][1].draft,true);
  assert.equal(f.calls.at(-1)[1].draft,false);
  assert.equal(f.calls.at(-1)[1].make_latest,'true');
});

test('published versions are not modified when later main commits keep the same version',async()=>{
  const f=fixture({existing:{id:1,draft:false,target_commitish:'old-commit'}});
  await f.run();assert.deepEqual(f.calls,[]);
});

test('asset failure leaves the release unpublished',async()=>{
  const f=fixture({failUpload:true});
  await assert.rejects(f.run(),/Upload failed/);
  assert.equal(f.calls.some(c=>c[0]==='publish'),false);
});

test('missing local assets fail before any release mutation',async()=>{
  const f=fixture({missingZip:true});
  await assert.rejects(f.run(),/Missing ZIP/);assert.deepEqual(f.calls,[]);
});

test('an existing tag pointing elsewhere is never moved',async()=>{
  const f=fixture({tagSha:'b'.repeat(40)});
  await assert.rejects(f.run(),/will not be moved/);assert.deepEqual(f.calls,[]);
});

test('drafts for another commit are not silently reused',async()=>{
  const f=fixture({existing:{id:1,draft:true,target_commitish:'other-commit'}});
  await assert.rejects(f.run(),/another commit/);assert.deepEqual(f.calls,[]);
});

test('a failed draft for this commit can be retried',async()=>{
  const f=fixture({existing:{id:1,draft:true,target_commitish:'a'.repeat(40)},tagSha:'a'.repeat(40)});
  await f.run();assert.deepEqual(f.calls.map(c=>c[0]),['upload','upload','publish']);
});
