import { NavLink, Outlet } from "react-router-dom";
import { color, font, shadow, transition } from "../../theme/tokens.ts";

const navItems = [
  { to: "/", label: "Lobby" },
  { to: "/table", label: "Table" },
  { to: "/lab", label: "Lab" },
  { to: "/ranges", label: "Ranges" },
  { to: "/strategy", label: "Strategy" },
];

export function Layout() {
  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        {/* Brand */}
        <span style={styles.brand}>
          <span style={styles.brandAccent}>UP</span>
          <span style={styles.brandSep}>//</span>
          <span style={styles.brandText}>Upstream People</span>
        </span>

        {/* Links */}
        <div style={styles.links}>
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
        </div>

        {/* Status indicator — decorative */}
        <div style={styles.statusDot} title="Engine ready" />
      </nav>

      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    background: color.gradient.page,
  },

  nav: {
    display: "flex",
    alignItems: "center",
    padding: "0 2rem",
    height: 48,
    background: color.gradient.nav,
    borderBottom: `1px solid ${color.bg.border}`,
    position: "relative" as const,
    zIndex: 10,
  },

  brand: {
    display: "flex",
    alignItems: "center",
    gap: "0.35rem",
    marginRight: "2.5rem",
    fontFamily: font.mono,
    fontSize: "0.8rem",
    letterSpacing: "0.06em",
  },

  brandAccent: {
    color: color.accent.gold,
    fontWeight: 700,
  },

  brandSep: {
    color: color.text.dim,
    fontWeight: 400,
  },

  brandText: {
    color: color.text.secondary,
    fontWeight: 400,
    textTransform: "uppercase" as const,
  },

  links: {
    display: "flex",
    alignItems: "center",
    gap: "0.25rem",
    flex: 1,
  },

  link: {
    fontSize: "0.72rem",
    fontWeight: 500,
    fontFamily: font.mono,
    color: color.text.muted,
    textDecoration: "none",
    padding: "0.35rem 0.75rem",
    borderRadius: 6,
    letterSpacing: "0.05em",
    textTransform: "uppercase" as const,
    transition: transition.fast,
    border: `1px solid transparent`,
  } as React.CSSProperties,

  activeLink: {
    color: color.text.primary,
    background: color.bg.elevated,
    border: `1px solid ${color.bg.border}`,
  },

  statusDot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    background: color.status.online,
    boxShadow: shadow.glow(color.status.online),
  },

  main: {
    flex: 1,
    overflow: "auto",
  },
};
