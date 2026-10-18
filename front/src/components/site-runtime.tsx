import { LoadingController } from "@/components/loading-controller";
import { NavbarController } from "@/components/navbar-controller";

export function SiteRuntime() {
  return (
    <>
      <LoadingController />
      <NavbarController />
    </>
  );
}
