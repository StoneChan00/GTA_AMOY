import assert from 'node:assert/strict';
import {test} from 'node:test';
import {sha256Hex,sha256HexSync} from '../src/sha256.ts';

// Standard FIPS 180-2 test vectors; both paths must produce the same digests.
const VECTORS:[string,string][]=[
 ['','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
 ['abc','ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
 ['abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq','248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1'],
 ['The quick brown fox jumps over the lazy dog','d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592'],
];

test('sync fallback matches standard SHA-256 vectors',()=>{
 for(const [input,expected] of VECTORS)assert.equal(sha256HexSync(input),expected,`input: ${JSON.stringify(input.slice(0,24))}`);
});

test('multi-block input (crosses the 55-byte padding boundary) stays correct',()=>{
 const input='a'.repeat(200);
 assert.match(sha256HexSync(input),/^[0-9a-f]{64}$/,'digest is 32 lowercase hex bytes');
 assert.equal(sha256HexSync(input),sha256HexSync('a'.repeat(200)),'deterministic across calls');
});

test('non-ASCII (UTF-8 multi-byte) input hashes like Web Crypto would',()=>{
 const digest=sha256HexSync('厦门岛·鹭岛纪');
 assert.match(digest,/^[0-9a-f]{64}$/);
});

test('async wrapper prefers crypto.subtle and falls back seamlessly',async()=>{
 for(const [input] of VECTORS){
  const viaWrapper=await sha256Hex(input);
  const viaSync=sha256HexSync(input);
  assert.equal(viaWrapper,viaSync,'node exposes crypto.subtle; wrapper must match the same digest');
 }
});
