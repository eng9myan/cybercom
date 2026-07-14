/**
 * Root navigation. ADR-0033 (mobile architecture).
 * Unauthenticated → Auth stack. Authenticated → App stack.
 */
import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { useAuth } from "../contexts/auth";

export type RootStackParamList = {
  Login: undefined;
  Dashboard: undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

function AuthStack() {
  const LoginScreen = require("../screens/LoginScreen").default as React.ComponentType;
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
    </Stack.Navigator>
  );
}

function AppStack() {
  const DashboardScreen = require("../screens/DashboardScreen").default as React.ComponentType;
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: "لوحة التحكم — Dashboard" }}
      />
    </Stack.Navigator>
  );
}

export function RootNavigator() {
  const { isAuthenticated } = useAuth();
  return (
    <NavigationContainer>
      {isAuthenticated ? <AppStack /> : <AuthStack />}
    </NavigationContainer>
  );
}
