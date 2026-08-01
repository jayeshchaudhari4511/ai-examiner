import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Button, buttonVariants } from "./button";
import { cn } from "../../lib/utils";
import { MenuToggleIcon } from "./menu-toggle-icon";
import { useScroll } from "./use-scroll";
import { createPortal } from "react-dom";
import { PenLine } from "lucide-react";
import { getStoredUser, clearStoredUser } from "../../services/authStorage";
import { clearAuthTokens } from "../../services/api";

export function Header() {
  const [open, setOpen] = React.useState(false);
  const scrolled = useScroll(10);
  const location = useLocation();
  const user = getStoredUser();
  const role = user?.role;

  const dashboardHref =
    role === "student"
      ? "/student"
      : role === "teacher"
      ? "/teacher"
      : role === "admin"
      ? "/admin"
      : "/dashboard";

  const links = [
    { label: "Home", href: "/" },
    ...(user ? [{ label: "Dashboard", href: dashboardHref }] : []),
    ...(user ? [{ label: "History", href: "/history" }] : []),
    ...(user && role === "admin" ? [{ label: "Management", href: "/management" }] : []),
  ];

  const evaluateLink =
    role === "teacher"
      ? { label: "Evaluate Now", href: "/evaluate" }
      : role === "admin"
      ? { label: "Evaluate Now", href: "/evaluate" }
      : null;

  const authLinks = [
    !user ? { label: "Login", href: "/login" } : null,
    !user ? { label: "Register", href: "/register" } : null,
  ].filter(Boolean) as { label: string; href: string }[];

  const handleLogout = () => {
    clearAuthTokens();
    clearStoredUser();
  };

  React.useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={cn("sticky top-0 z-50 w-full border-b border-transparent", {
        "bg-background/95 supports-[backdrop-filter]:bg-background/50 border-border backdrop-blur-lg":
          scrolled,
      })}
    >
      <nav className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 rounded-md p-2 hover:bg-accent">
          <PenLine className="h-4 w-4" />
          <span className="text-sm font-semibold tracking-wide">AI Examiner</span>
        </Link>
        <div className="hidden items-center gap-2 md:flex">
          {links.map((link) => (
            <Link
              key={link.label}
              className={cn(buttonVariants({ variant: "ghost" }),
                location.pathname === link.href && "text-foreground")}
              to={link.href}
            >
              {link.label}
            </Link>
          ))}
          {authLinks.map((link) => (
            <Link
              key={link.label}
              className={cn(buttonVariants({ variant: "ghost" }),
                location.pathname === link.href && "text-foreground")}
              to={link.href}
            >
              {link.label}
            </Link>
          ))}
          {user && (
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          )}
          {evaluateLink && (
            <Button asChild>
              <Link to={evaluateLink.href}>{evaluateLink.label}</Link>
            </Button>
          )}
        </div>
        <Button
          size="icon"
          variant="outline"
          onClick={() => setOpen(!open)}
          className="md:hidden"
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label="Toggle menu"
        >
          <MenuToggleIcon open={open} className="size-5" duration={300} />
        </Button>
      </nav>
      <MobileMenu open={open} className="flex flex-col justify-between gap-2">
        <div className="grid gap-y-2">
          {links.map((link) => (
            <Link
              key={link.label}
              className={buttonVariants({
                variant: "ghost",
                className: "justify-start",
              })}
              to={link.href}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          {authLinks.map((link) => (
            <Link
              key={link.label}
              className={buttonVariants({
                variant: "ghost",
                className: "justify-start",
              })}
              to={link.href}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <div className="flex flex-col gap-2">
          {user && (
            <Button
              className="w-full"
              variant="outline"
              onClick={() => {
                handleLogout();
                setOpen(false);
              }}
            >
              Logout
            </Button>
          )}
          {evaluateLink && (
            <Button asChild className="w-full bg-transparent" variant="outline">
              <Link to={evaluateLink.href} onClick={() => setOpen(false)}>
                {evaluateLink.label}
              </Link>
            </Button>
          )}
        </div>
      </MobileMenu>
    </header>
  );
}

type MobileMenuProps = React.ComponentProps<"div"> & {
  open: boolean;
};

function MobileMenu({ open, children, className, ...props }: MobileMenuProps) {
  if (!open || typeof window === "undefined") return null;

  return createPortal(
    <div
      id="mobile-menu"
      className={cn(
        "bg-background/95 supports-[backdrop-filter]:bg-background/50 backdrop-blur-lg",
        "fixed inset-x-0 bottom-0 top-14 z-40 flex flex-col overflow-hidden border-y md:hidden"
      )}
    >
      <div
        data-slot={open ? "open" : "closed"}
        className={cn(
          "data-[slot=open]:animate-in data-[slot=open]:zoom-in-97 ease-out",
          "size-full p-4",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </div>,
    document.body
  );
}
