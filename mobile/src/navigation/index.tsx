/**
 * Root navigation. ADR-0033 (mobile architecture).
 * Unauthenticated → Auth stack. Authenticated → App stack.
 */
import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { useAuth } from "../contexts/auth";
import LoginScreen from "../screens/LoginScreen";
import DashboardScreen from "../screens/DashboardScreen";
import CategoriesScreen from "../screens/CategoriesScreen";
import CartScreen from "../screens/CartScreen";
import OrdersScreen from "../screens/OrdersScreen";

export type AuthStackParamList = {
  Login: undefined;
};

export type AppStackParamList = {
  Dashboard: undefined;
  Categories: undefined;
  Cart: undefined;
  Orders: undefined;
};

const AuthStackNav = createNativeStackNavigator<AuthStackParamList>();
const AppStackNav = createNativeStackNavigator<AppStackParamList>();

function AuthStack() {
  return (
    <AuthStackNav.Navigator screenOptions={{ headerShown: false }}>
      <AuthStackNav.Screen name="Login" component={LoginScreen} />
    </AuthStackNav.Navigator>
  );
}

function AppStack() {
  return (
    <AppStackNav.Navigator>
      <AppStackNav.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: "لوحة التحكم — Dashboard" }}
      />
      <AppStackNav.Screen
        name="Categories"
        component={CategoriesScreen}
        options={{ title: "CyMart" }}
      />
      <AppStackNav.Screen name="Cart" component={CartScreen} options={{ title: "Cart" }} />
      <AppStackNav.Screen name="Orders" component={OrdersScreen} options={{ title: "My Orders" }} />
    </AppStackNav.Navigator>
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
