import { useCallback, useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { AuthContext } from "../lib/auth-context";
import type { Profile } from "../lib/roles";

/**
 * Menyediakan data pengguna yang sedang login ke seluruh aplikasi.
 * Profil diambil dari tabel `profiles` (dijaga RLS: hanya staf aktif).
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let aktif = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!aktif) return;
      setSession(data.session);
      if (!data.session) setLoading(false);
    });

    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      if (!next) {
        setProfile(null);
        setLoading(false);
      }
    });

    return () => {
      aktif = false;
      sub.subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    let aktif = true;
    if (!session?.user) {
      setProfile(null);
      return;
    }
    setLoading(true);
    supabase
      .from("profiles")
      .select("id, full_name, role, gender, is_active")
      .eq("id", session.user.id)
      .maybeSingle()
      .then(({ data, error }) => {
        if (!aktif) return;
        if (error || !data) {
          setProfile(null);
        } else {
          setProfile(data as Profile);
        }
        setLoading(false);
      });
    return () => {
      aktif = false;
    };
  }, [session]);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setProfile(null);
  }, []);

  return (
    <AuthContext.Provider value={{ profile, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}