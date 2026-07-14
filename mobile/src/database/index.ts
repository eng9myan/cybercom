import { Database } from '@nozbe/watermelondb';
import { appSchema } from '@nozbe/watermelondb/Schema';
import SQLiteAdapter from '@nozbe/watermelondb/adapters/sqlite';

// No offline tables defined yet — real local schema (cart, orders, sync
// queue per master spec section 21) is still open work, not invented here.
// appSchema()/tableSchema() are WatermelonDB's real schema constructors;
// the previous version of this file built a plain { tables: [] } object by
// hand, which doesn't satisfy WatermelonDB's TableMap type (caught by
// `tsc --noEmit`, which had never been run against this file before).
const schema = appSchema({
  version: 1,
  tables: [],
});

const adapter = new SQLiteAdapter({
  dbName: 'cybercom_local',
  schema,
  // In production, passes encryptionKey to SQLCipher library binding
});

export const database = new Database({
  adapter,
  modelClasses: [],
});
