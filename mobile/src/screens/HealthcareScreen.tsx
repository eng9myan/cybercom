/**
 * CyID ecosystem, Phase 9 — real medical orders (lab/imaging/medication/
 * procedure/referral) for the session's active tenant. See
 * src/api/cymed.ts for the real, honest scope limit: this is one
 * tenant at a time, not a cross-network "everywhere I've ever been seen"
 * view — that needs a PersonIdentity↔Patient link that doesn't exist yet.
 */
import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { useAuth } from "../contexts/auth";
import { cymedApi, CymedOrder } from "../api/cymed";

const TYPE_LABELS: Record<CymedOrder["order_type"], string> = {
  laboratory: "Lab",
  imaging: "Imaging",
  medication: "Medication",
  procedure: "Procedure",
  referral: "Referral",
};

export default function HealthcareScreen() {
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
        const result = await cymedApi.listOrders(session.accessToken, session.tenantId);
        if (!cancelled) setOrders(result.results);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load your medical records.");
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
              <Text style={styles.rowTitle}>{TYPE_LABELS[item.order_type]}</Text>
              <Text style={styles.status}>{item.status}</Text>
              <Text style={styles.rowSub}>Ordered by {item.ordered_by}</Text>
              <Text style={styles.rowSub}>{new Date(item.ordered_at).toLocaleString()}</Text>
              {item.fulfilling_tenant_id ? (
                <Text style={styles.fulfillTag}>Fulfilled externally</Text>
              ) : null}
            </View>
          )}
          ListEmptyComponent={<Text style={styles.empty}>No medical records at this workspace yet.</Text>}
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
