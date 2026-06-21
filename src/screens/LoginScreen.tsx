import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

export default function LoginScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>CyberCom</Text>
      <Text style={styles.subtitle}>Enterprise Platform</Text>
      <TouchableOpacity style={styles.loginBtn}>
        <Text style={styles.loginBtnText}>تسجيل الدخول / Sign In</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0f1117" },
  title: { fontSize: 32, fontWeight: "bold", color: "#ffffff", marginBottom: 8 },
  subtitle: { fontSize: 16, color: "#9ca3af", marginBottom: 48 },
  loginBtn: { backgroundColor: "#2563eb", paddingHorizontal: 32, paddingVertical: 14, borderRadius: 8 },
  loginBtnText: { color: "#ffffff", fontSize: 16, fontWeight: "600" },
});
