import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { Discover } from "./pages/Discover";
import { HealthPlus } from "./pages/HealthPlus";
import { Scan } from "./pages/Scan";
import { Profile } from "./pages/Profile";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Discover },
      { path: "health", Component: HealthPlus },
      { path: "scan", Component: Scan },
      { path: "profile", Component: Profile },
    ],
  },
]);
