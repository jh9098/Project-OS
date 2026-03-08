export type NavItem = {
  href: string;
  label: string;
};

export const PRIMARY_NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/tasks", label: "Tasks" },
  { href: "/relations", label: "Relations" },
  { href: "/notes", label: "Notes" }
];

export const DESKTOP_NAV_ITEMS: NavItem[] = [...PRIMARY_NAV_ITEMS, { href: "/settings", label: "Settings" }];
