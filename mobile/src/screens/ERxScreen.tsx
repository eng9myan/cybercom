/**
 * CyID ecosystem, Phase 9 — active medication orders (e-Rx) at the
 * session's active tenant. Same real data source as HealthcareScreen
 * (products/cymed/core/orders), filtered server-side to order_type=medication
 * — depends on Phase 9's DEFAULT_FILTER_BACKENDS fix in cymed/core/settings.py
 * (that query param was previously silently ignored).
 */
import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { useAuth } from "../contexts/auth";
import { cymedApi, CymedOrder } from "../api/cymed";

export default function ERxScreen() {
  const { session } = useAuth();
  const [orders, setOrders] = useState<CymedOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!session) return;
      setLoading(true);
      setError(null);
      try {
        const result = await cymedApi.listOrders(session.accessToken, session.tenantId, {
          order_type: "medication",
        });
        if (!cancelled) setOrders(result.results);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load prescriptions.");
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
              <Text style={styles.rowTitle}>Prescription</Text>
              <Text style={styles.status}>{item.status}</Text>
              <Text style={styles.rowSub}>Prescribed by {item.ordered_by}</Text>
              <Text style={styles.rowSub}>{new Date(item.ordered_at).toLocaleString()}</Text>
              {item.fulfilling_tenant_id ? (
                <Text style={styles.fulfillTag}>Routed to a pharmacy for pickup</Text>
              ) : (
                <Text style={styles.fulfillTag}>Not yet routed to a pharmacy</Text>
              )}
            </View>
          )}
          ListEmptyComponent={<Text style={styles.empty}>No active prescriptions.</Text>}
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
  fulfillTag: { color: "#facc15", fontSize: 11, marginTop: 6, fontWeight: "600" },
  errorBox: { margin: 20, padding: 16, backgroundColor: "#7f1d1d", borderRadius: 8 },
  errorText: { color: "#fca5a5", textAlign: "center" },
  empty: { color: "#6b7280", textAlign: "center", marginTop: 40 },
});
