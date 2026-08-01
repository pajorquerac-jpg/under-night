import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

const queryClient = new QueryClient();

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar backgroundColor="#ffffff" style="light" translucent={false} />
      <Stack
        screenOptions={{
          //contentStyle: { backgroundColor: "#000000" },
          headerShown: false,
          //headerStyle: { backgroundColor: "#000000" },
          headerTintColor: "#FFFFFF",
          navigationBarColor: "#FFFFFF",
        }}
      />
    </QueryClientProvider>
  );
}
