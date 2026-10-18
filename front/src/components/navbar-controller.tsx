"use client";

import { useEffect } from "react";

export function NavbarController() {
  useEffect(() => {
    const header = document.querySelector<HTMLElement>(".header");
    const menuButton = document.querySelector<HTMLElement>(".header-menu-btn");
    const menuInner = document.querySelector<HTMLElement>(".header-menu-inner");
    const menuWrap = document.querySelector<HTMLElement>(".header-menu-wrap");
    const menu = document.querySelector<HTMLElement>(
      ".header-menu-wrap .header-menu",
    );
    const submenuItems = document.querySelectorAll<HTMLElement>(
      ".header-menu-item.has-submenu",
    );

    if (!header || !menuButton || !menuInner || !menuWrap || !menu) return;

    const setMobileMenu = (open: boolean) => {
      header.classList.toggle("nav-open", open);
      menuInner.classList.toggle("nav-open", open);
      menuWrap.classList.toggle("nav-open", open);
      menu.classList.toggle("nav-open", open);
      menu.style.pointerEvents = open ? "auto" : "";
      menuWrap.style.pointerEvents = open ? "auto" : "";
      menuButton.setAttribute("aria-expanded", String(open));
    };

    const setSubmenu = (item: HTMLElement, open: boolean) => {
      const dropdown = item.querySelector<HTMLElement>(".header-menu-dropdown");
      if (!dropdown) return;

      item.classList.toggle("nav-submenu-open", open);
      dropdown.classList.toggle("nav-submenu-open", open);
      dropdown.style.opacity = open ? "1" : "";
      dropdown.style.pointerEvents = open ? "auto" : "";
      dropdown.style.gridTemplateRows = open ? "1fr" : "";
    };

    const onMenuClick = (event: MouseEvent) => {
      event.preventDefault();
      setMobileMenu(!menuInner.classList.contains("nav-open"));
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileMenu(false);
        submenuItems.forEach((item) => setSubmenu(item, false));
      }
    };
    const onResize = () => {
      if (window.innerWidth > 767) setMobileMenu(false);
    };

    menuButton.addEventListener("click", onMenuClick);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("resize", onResize);

    const cleanups = [...submenuItems].map((item) => {
      const open = () => {
        if (window.innerWidth > 767) setSubmenu(item, true);
      };
      const close = () => {
        if (window.innerWidth > 767) setSubmenu(item, false);
      };
      item.addEventListener("mouseenter", open);
      item.addEventListener("mouseleave", close);
      return () => {
        item.removeEventListener("mouseenter", open);
        item.removeEventListener("mouseleave", close);
      };
    });

    return () => {
      menuButton.removeEventListener("click", onMenuClick);
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("resize", onResize);
      cleanups.forEach((cleanup) => cleanup());
    };
  }, []);

  return null;
}
