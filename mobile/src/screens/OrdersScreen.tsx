import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { useAuth } from "../contexts/auth";
import { cymartApi, MarketplaceOrder } from "../api/cymart";

export default function OrdersScreen() {
  const { session } = useAuth();
  const [orders, setOrders] = useState<MarketplaceOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!session) return;
      setLoading(true);
      setError(null);
      try {
        const result = await cymartApi.listOrders(session.accessToken, session.userId);
        if (!cancelled) setOrders(result.data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load orders.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [session]);

  return (
    <SafeAreaView style={styles.container}>
      {loading ? (
        <ActivityIndicator size="large" color="#2563eb" style={styles.loader} />
      ) : error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View style={styles.row}>
              <Text style={styles.rowTitle}>Order {item.id.slice(0, 8)}</Text>
              <Text style={styles.status}>{item.status}</Text>
              <Text style={styles.rowSub}>Total: {item.total_amount}</Text>
            </View>
          )}
          ListEmptyComponent={<Text style={styles.empty}>No orders yet.</Text>}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f1117" },
  loader: { marginTop: 40 },
  list: { padding: 16 },
  row: {
    backgroundColor: "#1e293b",
    borderRadius: 10,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#334155",
  },
  rowTitle: { color: "#fff", fontSize: 15, fontWeight: "600" },
  status: { color: "#2563eb", fontSize: 12, fontWeight: "700", marginTop: 4, textTransform: "uppercase" },
  rowSub: { color: "#9ca3af", fontSize: 12, marginTop: 4 },
  errorBox: { margin: 20, padding: 16, backgroundColor: "#7f1d1d", borderRadius: 8 },
  errorText: { color: "#fca5a5", textAlign: "center" },
  empty: { color: "#6b7280", textAlign: "center", marginTop: 40 },
});
