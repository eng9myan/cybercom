import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useAuth } from "../contexts/auth";
import type { AppStackParamList } from "../navigation";

type Props = NativeStackScreenProps<AppStackParamList, "Dashboard">;

const TILES: Array<{ key: keyof AppStackParamList; label: string; labelAr: string; icon: string }> = [
  { key: "Categories", label: "Shop CyMart", labelAr: "التسوق", icon: "🛍️" },
  { key: "Cart", label: "Cart", labelAr: "السلة", icon: "🛒" },
  { key: "Orders", label: "My Orders", labelAr: "طلباتي", icon: "📦" },
];

export default function DashboardScreen({ navigation }: Props) {
  const { session, logout } = useAuth();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.greeting}>مرحباً · Welcome</Text>
        <Text style={styles.email}>{session?.email}</Text>

        <View style={styles.grid}>
          {TILES.map((tile) => (
            <TouchableOpacity
              key={tile.key}
              style={styles.tile}
              onPress={() => navigation.navigate(tile.key as never)}
              accessibilityLabel={tile.label}
            >
              <Text style={styles.tileIcon}>{tile.icon}</Text>
              <Text style={styles.tileLabel}>{tile.label}</Text>
              <Text style={styles.tileLabelAr}>{tile.labelAr}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.logoutBtn} onPress={logout} accessibilityLabel="Sign out">
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f1117" },
  content: { padding: 20 },
  greeting: { fontSize: 24, fontWeight: "bold", color: "#fff" },
  email: { fontSize: 13, color: "#9ca3af", marginTop: 4, marginBottom: 24 },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  tile: {
    width: "47%",
    backgroundColor: "#1e293b",
    borderRadius: 12,
    padding: 20,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#334155",
  },
  tileIcon: { fontSize: 32, marginBottom: 8 },
  tileLabel: { color: "#fff", fontSize: 15, fontWeight: "600" },
  tileLabelAr: { color: "#9ca3af", fontSize: 12, marginTop: 2 },
  logoutBtn: { marginTop: 32, alignItems: "center", padding: 12 },
  logoutText: { color: "#ef4444", fontSize: 14, fontWeight: "600" },
});
