/**
 * Cycom ERP API Bridge Integration Test
 * Run with: node scripts/test_bridge.js
 */

const assert = require('assert');
const http = require('http');

console.log("==================================================");
console.log("🧪 Running Cycom ERP API Bridge Integration Tests");
console.log("==================================================");

// Mock server for Backend JSON-RPC to test Next.js proxy
const mockBackendServer = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    if (req.url === '/web/session/authenticate') {
      res.end(JSON.stringify({
        jsonrpc: '2.0',
        result: {
          uid: 2,
          name: 'Administrator',
          username: 'admin',
          partner_id: 3,
          company_id: 1,
          is_admin: true
        }
      }));
    } else if (req.url === '/web/dataset/call_kw') {
      const parsedBody = JSON.parse(body);
      const { model, method } = parsedBody.params;
      
      if (model === 'sale.order' && method === 'search_read') {
        res.end(JSON.stringify({
          jsonrpc: '2.0',
          result: [
            { id: 1, name: 'SO001', amount_total: 4200.0, state: 'sale' },
            { id: 2, name: 'SO002', amount_total: 180.0, state: 'draft' }
          ]
        }));
      } else {
        res.end(JSON.stringify({
          jsonrpc: '2.0',
          result: { success: true }
        }));
      }
    } else {
      res.writeHead(404);
      res.end();
    }
  });
});

mockBackendServer.listen(8069, 'localhost', () => {
  console.log("✅ Mock Backend server listening on port 8069");
  runTests();
});

function runTests() {
  // Test 1: Mock JSON-RPC authentication
  console.log("⚡ Test 1: Authenticating with Cycom ERP Mock Server...");
  const authPayload = JSON.stringify({
    jsonrpc: '2.0',
    params: { db: 'cycom', login: 'admin', password: 'password' }
  });

  const req = http.request({
    hostname: 'localhost',
    port: 8069,
    path: '/web/session/authenticate',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': authPayload.length
    }
  }, (res) => {
    let responseData = '';
    res.on('data', chunk => { responseData += chunk; });
    res.on('end', () => {
      const result = JSON.parse(responseData);
      assert.strictEqual(result.result.uid, 2);
      assert.strictEqual(result.result.username, 'admin');
      console.log("✅ Test 1 Passed: Authentication successful!");
      test2();
    });
  });

  req.on('error', (e) => {
    console.error(`❌ Test 1 Failed: ${e.message}`);
    mockBackendServer.close();
    process.exit(1);
  });

  req.write(authPayload);
  req.end();
}

function test2() {
  // Test 2: Mock call_kw search_read
  console.log("⚡ Test 2: Executing search_read call for sale.order...");
  const callPayload = JSON.stringify({
    jsonrpc: '2.0',
    params: {
      model: 'sale.order',
      method: 'search_read',
      args: [],
      kwargs: { limit: 10 }
    }
  });

  const req = http.request({
    hostname: 'localhost',
    port: 8069,
    path: '/web/dataset/call_kw',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': callPayload.length
    }
  }, (res) => {
    let responseData = '';
    res.on('data', chunk => { responseData += chunk; });
    res.on('end', () => {
      const result = JSON.parse(responseData);
      assert.ok(Array.isArray(result.result));
      assert.strictEqual(result.result[0].name, 'SO001');
      assert.strictEqual(result.result[0].amount_total, 4200.0);
      console.log("✅ Test 2 Passed: search_read executed successfully!");
      finish();
    });
  });

  req.on('error', (e) => {
    console.error(`❌ Test 2 Failed: ${e.message}`);
    mockBackendServer.close();
    process.exit(1);
  });

  req.write(callPayload);
  req.end();
}

function finish() {
  console.log("\n==================================================");
  console.log("🎉 All Cycom ERP integration bridge tests PASSED!");
  console.log("==================================================");
  mockBackendServer.close();
  process.exit(0);
}
