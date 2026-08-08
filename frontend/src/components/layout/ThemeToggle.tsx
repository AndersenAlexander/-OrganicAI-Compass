import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";

type ThemeToggleProps = {
  className?: string;
};

export function ThemeToggle({ className = "" }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`relative flex h-10 w-[72px] shrink-0 items-center rounded-full border border-white/15 bg-white/8 p-1 text-[#99f6e4] transition hover:bg-white/12 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#5eead4] ${className}`}
      title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
      aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
    >
      <span
        className={`absolute top-1 grid h-8 w-8 place-items-center rounded-full bg-white text-[#071527] shadow transition ${
          theme === "dark" ? "left-[38px]" : "left-1"
        }`}
      >
        {theme === "light" ? <Sun size={16} /> : <Moon size={16} />}
      </span>
      <Sun size={15} className="ml-2 opacity-80" />
      <Moon size={15} className="ml-auto mr-2 opacity-80" />
    </button>
  );
}
