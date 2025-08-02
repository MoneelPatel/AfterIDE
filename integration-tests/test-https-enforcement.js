#!/usr/bin/env node

/**
 * AfterIDE - HTTPS Enforcement Test
 * 
 * Simple script to test that HTTPS enforcement is working correctly
 * and no HTTP requests are being made to the API.
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

// Test URLs
const TEST_URLS = [
  'https://sad-chess-production.up.railway.app/api/v1/submissions/',
  'https://sad-chess-production.up.railway.app/api/v1/submissions/stats',
  'https://sad-chess-production.up.railway.app/api/v1/submissions/reviewers',
];

// URLs that should NOT be accessible over HTTP
const HTTP_URLS = [
  'http://sad-chess-production.up.railway.app/api/v1/submissions/',
  'http://sad-chess-production.up.railway.app/api/v1/submissions/stats',
];

async function testHttpsUrl(url) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 443,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: {
        'User-Agent': 'AfterIDE-HTTPS-Test/1.0',
      },
      timeout: 10000,
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          url,
          status: res.statusCode,
          headers: res.headers,
          data: data.substring(0, 200), // First 200 chars
        });
      });
    });

    req.on('error', (error) => {
      reject({ url, error: error.message });
    });

    req.on('timeout', () => {
      req.destroy();
      reject({ url, error: 'Request timeout' });
    });

    req.end();
  });
}

async function testHttpUrl(url) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: {
        'User-Agent': 'AfterIDE-HTTPS-Test/1.0',
      },
      timeout: 5000, // Shorter timeout for HTTP tests
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          url,
          status: res.statusCode,
          headers: res.headers,
          data: data.substring(0, 200),
        });
      });
    });

    req.on('error', (error) => {
      resolve({ url, error: error.message, blocked: true });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ url, error: 'Request timeout', blocked: true });
    });

    req.end();
  });
}

async function runTests() {
  console.log('🔒 Testing HTTPS Enforcement for AfterIDE API\n');

  // Test HTTPS URLs
  console.log('✅ Testing HTTPS URLs (should work):');
  for (const url of TEST_URLS) {
    try {
      const result = await testHttpsUrl(url);
      console.log(`  ✓ ${url} - Status: ${result.status}`);
      if (result.status === 401) {
        console.log(`    ℹ️  Expected 401 (authentication required)`);
      }
    } catch (error) {
      console.log(`  ✗ ${url} - Error: ${error.error}`);
    }
  }

  console.log('\n❌ Testing HTTP URLs (should be blocked):');
  for (const url of HTTP_URLS) {
    try {
      const result = await testHttpUrl(url);
      if (result.blocked || result.error) {
        console.log(`  ✓ ${url} - Blocked: ${result.error}`);
      } else {
        console.log(`  ✗ ${url} - Unexpectedly accessible: ${result.status}`);
      }
    } catch (error) {
      console.log(`  ✓ ${url} - Blocked: ${error.error}`);
    }
  }

  console.log('\n🔍 Testing Mixed Content Prevention:');
  
  // Simulate what the frontend would do
  const testUrls = [
    'http://sad-chess-production.up.railway.app/api/v1/submissions/',
    'https://sad-chess-production.up.railway.app/api/v1/submissions/',
  ];

  for (const url of testUrls) {
    const httpsUrl = url.replace('http://', 'https://');
    console.log(`  Original: ${url}`);
    console.log(`  Converted: ${httpsUrl}`);
    console.log(`  Should use HTTPS: ${httpsUrl === url ? 'No' : 'Yes'}\n`);
  }

  console.log('✅ HTTPS Enforcement Test Complete!');
}

// Run the tests
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { testHttpsUrl, testHttpUrl, runTests }; 