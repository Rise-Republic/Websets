import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useGlobalStore } from "@/store/global";

export default function useTenantGuard() {
  const tenantId = useGlobalStore((s) => s.tenantId);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const routeTenant = params.get("tenant");
    if (routeTenant && tenantId && routeTenant !== tenantId) {
      navigate("/");
    }
  }, [location, tenantId, navigate]);
}
