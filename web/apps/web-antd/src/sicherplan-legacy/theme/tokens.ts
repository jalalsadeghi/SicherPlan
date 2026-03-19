import { webAppConfig } from "@/config/env";

export type ThemeMode = "light" | "dark";

export interface ThemeTokens {
  mode: ThemeMode;
  primary: string;
  primaryStrong: string;
  primaryMuted: string;
  success: string;
  warning: string;
  danger: string;
  surfacePage: string;
  surfacePanel: string;
  surfaceCard: string;
  surfaceSidebar: string;
  borderSoft: string;
  textPrimary: string;
  textSecondary: string;
  textInverse: string;
  shadowCard: string;
  heroGradient: string;
  pageBackground: string;
}

export const themeTokens: Record<ThemeMode, ThemeTokens> = {
  light: {
    mode: "light",
    primary: webAppConfig.lightPrimary,
    primaryStrong: "rgb(17,111,111)",
    primaryMuted: "rgba(40,170,170,0.14)",
    success: "rgb(46,148,110)",
    warning: "rgb(194,137,37)",
    danger: "rgb(185,78,78)",
    surfacePage: "rgb(244,247,248)",
    surfacePanel: "rgba(255,255,255,0.82)",
    surfaceCard: "rgba(255,255,255,0.9)",
    surfaceSidebar: "rgba(11,54,56,0.92)",
    borderSoft: "rgba(21,74,75,0.12)",
    textPrimary: "rgb(24,53,53)",
    textSecondary: "rgb(70,100,100)",
    textInverse: "rgb(238,248,247)",
    shadowCard: "0 18px 40px rgba(24,53,53,0.10)",
    heroGradient:
      "linear-gradient(135deg, rgba(40,170,170,0.14), rgba(18,109,109,0.10))",
    pageBackground:
      "radial-gradient(circle at top left, rgba(40,170,170,0.25), transparent 30%), linear-gradient(160deg, #f2f9f8 0%, #e4f1ef 55%, #d9ece8 100%)",
  },
  dark: {
    mode: "dark",
    primary: webAppConfig.darkPrimary,
    primaryStrong: "rgb(18,123,128)",
    primaryMuted: "rgba(35,200,205,0.18)",
    success: "rgb(79,186,141)",
    warning: "rgb(225,178,74)",
    danger: "rgb(222,111,111)",
    surfacePage: "rgb(8,18,20)",
    surfacePanel: "rgba(18,32,35,0.88)",
    surfaceCard: "rgba(18,32,35,0.94)",
    surfaceSidebar: "rgba(10,20,23,0.96)",
    borderSoft: "rgba(203,241,242,0.12)",
    textPrimary: "rgb(230,245,245)",
    textSecondary: "rgb(151,181,182)",
    textInverse: "rgb(8,18,20)",
    shadowCard: "0 18px 44px rgba(0,0,0,0.28)",
    heroGradient:
      "linear-gradient(135deg, rgba(35,200,205,0.18), rgba(14,72,78,0.36))",
    pageBackground:
      "radial-gradient(circle at top left, rgba(35,200,205,0.16), transparent 28%), linear-gradient(160deg, #081214 0%, #0d1f22 58%, #11262a 100%)",
  },
};
