import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useAuth } from "../contexts/auth";
import { cymartApi, Category } from "../api/cymart";

export default function CategoriesScreen() {
  const { session } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!session) return;
      setLoading(true);
      setError(null);
      try {
        const result = await cymartApi.listCategories(session.accessToken);
        if (!cancelled) setCategories(result.data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load categories.");
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
          data={categories}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.row} accessibilityLabel={item.name_en}>
              <View>
                <Text style={styles.rowTitle}>{item.name_en}</Text>
                {item.name_ar ? <Text style={styles.rowTitleAr}>{item.name_ar}</Text> : null}
              </View>
              {item.is_restricted ? <Text style={styles.restrictedBadge}>Restricted</Text> : null}
            </TouchableOpacity>
          )}
          ListEmptyComponent={<Text style={styles.empty}>No categories available.</Text>}
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
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#1e293b",
    borderRadius: 10,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#334155",
  },
  rowTitle: { color: "#fff", fontSize: 15, fontWeight: "600" },
  rowTitleAr: { color: "#9ca3af", fontSize: 12, marginTop: 2 },
  restrictedBadge: { color: "#f59e0b", fontSize: 11, fontWeight: "600" },
  errorBox: { margin: 20, padding: 16, backgroundColor: "#7f1d1d", borderRadius: 8 },
  errorText: { color: "#fca5a5", textAlign: "center" },
  empty: { color: "#6b7280", textAlign: "center", marginTop: 40 },
});
