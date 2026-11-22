import { createContext, useContext } from "react";
import type { Profile } from "./roles";

export interface AuthState {
  /** Profil pengguna yang sedang login; null bila belum login atau belum aktif. */
  profile: Profile | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

export const AuthContext = createContext<AuthState>({
  profile: null,
  loading: true,
  signOut: async () => {},
});

export function useAuth(): AuthState {
  return useContext(AuthContext);
}