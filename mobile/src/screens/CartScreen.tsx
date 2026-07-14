import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useAuth } from "../contexts/auth";
import { cymartApi, Cart } from "../api/cymart";
import { ApiError } from "../api/client";

export default function CartScreen() {
  const { session } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const result = await cymartApi.getActiveCart(session.accessToken);
      setCart(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cart.");
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCheckout() {
    if (!session || !cart) return;
    setCheckingOut(true);
    try {
      const result = await cymartApi.checkout(session.accessToken, cart.id);
      Alert.alert("Order placed", `Order ${result.order_id} — ${result.status}`);
      load();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.problem?.detail ?? err.message : String(err);
      Alert.alert("Checkout failed", message);
    } finally {
      setCheckingOut(false);
    }
  }

  const total = (cart?.items ?? []).reduce(
    (sum, item) =>
      sum + (parseFloat(item.unit_price) * parseFloat(item.quantity) - parseFloat(item.item_discount)),
    0
  );

  return (
    <SafeAreaView style={styles.container}>
      {loading ? (
        <ActivityIndicator size="large" color="#2563eb" style={styles.loader} />
      ) : error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : (
        <>
          <FlatList
            data={cart?.items ?? []}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => (
              <View style={styles.row}>
                <View>
                  <Text style={styles.rowTitle}>{item.product_name_snapshot || item.product_id}</Text>
                  <Text style={styles.rowSub}>
                    {item.quantity} × {item.unit_price}
                  </Text>
                </View>
              </View>
            )}
            ListEmptyComponent={<Text style={styles.empty}>Your cart is empty.</Text>}
          />
          <View style={styles.footer}>
            <Text style={styles.total}>Total: {total.toFixed(2)}</Text>
            <TouchableOpacity
              style={[styles.checkoutBtn, (!cart || cart.items.length === 0) && styles.disabled]}
              onPress={handleCheckout}
              disabled={!cart || cart.items.length === 0 || checkingOut}
              accessibilityLabel="Checkout"
            >
              {checkingOut ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.checkoutText}>Checkout</Text>
              )}
            </TouchableOpacity>
          </View>
        </>
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
  rowSub: { color: "#9ca3af", fontSize: 12, marginTop: 4 },
  footer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: "#334155",
  },
  total: { color: "#fff", fontSize: 16, fontWeight: "700", marginBottom: 12 },
  checkoutBtn: {
    backgroundColor: "#2563eb",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
  },
  disabled: { opacity: 0.5 },
  checkoutText: { color: "#fff", fontSize: 15, fontWeight: "700" },
  errorBox: { margin: 20, padding: 16, backgroundColor: "#7f1d1d", borderRadius: 8 },
  errorText: { color: "#fca5a5", textAlign: "center" },
  empty: { color: "#6b7280", textAlign: "center", marginTop: 40 },
});
