import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, SafeAreaView, ActivityIndicator } from 'react-native';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [pendingCount, setPendingCount] = useState<number>(3); // Mock local outbox items
  const [networkStatus, setNetworkStatus] = useState<'Online' | 'Offline'>('Offline');

  const triggerBiometricUnlock = () => {
    // Biometric scanner placeholder - simulates enclave verification
    setIsAuthenticated(true);
  };

  const executeQueueSync = () => {
    if (networkStatus === 'Offline') {
      alert('Device is offline. Outbox transactions queued.');
      return;
    }
    setIsSyncing(true);
    setTimeout(() => {
      setPendingCount(0);
      setIsSyncing(false);
      alert('Sync successful! Database aligned.');
    }, 2000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>CyberCom Mobile Portal</Text>
        <Text style={styles.subtitle}>Secure Offline-First Clinician & Citizen Shell</Text>
      </View>

      {!isAuthenticated ? (
        <View style={styles.authContainer}>
          <Text style={styles.authLabel}>Access Gated. Unlock Required.</Text>
          <TouchableOpacity style={styles.button} onPress={triggerBiometricUnlock}>
            <Text style={styles.buttonText}>Authenticate (Biometric Touch)</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.dashboard}>
          <View style={styles.statusRow}>
            <Text style={styles.label}>Network State:</Text>
            <TouchableOpacity onPress={() => setNetworkStatus(networkStatus === 'Online' ? 'Offline' : 'Online')}>
              <Text style={[styles.value, networkStatus === 'Online' ? styles.online : styles.offline]}>
                {networkStatus} (Toggle)
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.statusRow}>
            <Text style={styles.label}>SQLCipher local Database:</Text>
            <Text style={[styles.value, styles.secured]}>Encrypted (AES-256)</Text>
          </View>

          <View style={styles.statusRow}>
            <Text style={styles.label}>Pending Sync Queue:</Text>
            <Text style={styles.value}>{pendingCount} transactions</Text>
          </View>

          {isSyncing ? (
            <ActivityIndicator size="large" color="#00579b" style={{ marginVertical: 20 }} />
          ) : (
            <TouchableOpacity style={[styles.button, styles.syncBtn]} onPress={executeQueueSync}>
              <Text style={styles.buttonText}>Sync Outbox Queue</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginVertical: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#01579b',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  authContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  authLabel: {
    fontSize: 16,
    marginBottom: 20,
    color: '#333',
  },
  button: {
    backgroundColor: '#01579b',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  syncBtn: {
    backgroundColor: '#2e7d32',
    marginTop: 30,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  dashboard: {
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 3,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  label: {
    fontSize: 14,
    color: '#555',
    fontWeight: '500',
  },
  value: {
    fontSize: 14,
    color: '#111',
    fontWeight: 'bold',
  },
  online: {
    color: '#2e7d32',
  },
  offline: {
    color: '#c62828',
  },
  secured: {
    color: '#01579b',
  },
});
