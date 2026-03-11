import { NavLink, Outlet } from "react-router-dom";
import { color, font } from "../../theme/tokens.ts";

const navItems = [
  { to: "/", label: "Lobby" },
  { to: "/table", label: "Table" },
  { to: "/lab", label: "Lab" },
  { to: "/ranges", label: "Ranges" },
  { to: "/strategy", label: "Strategy" },
];

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    gap: "2rem",
    padding: "0.75rem 2rem",
    background: color.bg.surface,
    borderBottom: `1px solid ${color.bg.elevated}`,
  },
  brand: {
    fontFamily: font.mono,
    fontSize: "0.85rem",
    fontWeight: 600,
    color: color.accent.emerald,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    marginRight: "2rem",
  },
  link: {
    fontSize: "0.8rem",
    fontWeight: 500,
    color: color.text.secondary,
    textDecoration: "none",
    padding: "0.25rem 0",
    letterSpacing: "0.04em",
    textTransform: "uppercase" as const,
    borderBottom: "2px solid transparent",
    transition: "color 0.15s, border-color 0.15s",
  },
  activeLink: {
    color: color.text.primary,
    borderBottomColor: color.accent.gold,
  },
  main: {
    flex: 1,
    overflow: "auto",
  },
};

export function Layout() {
  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        <span style={styles.brand}>Upstream People</span>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive ? styles.activeLink : {}),
            })}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
