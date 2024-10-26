import {
  Navbar, 
  NavbarBrand, 
  NavbarContent, 
  NavbarItem, 
  Link, 
  Button,
  NavbarMenuToggle,
  NavbarMenu,
} from "@nextui-org/react";
import { useState } from "react";

export default function NavBar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const menuItems = [
    { name: "Home Page", href: "/" },
    { name: "About Us", href: "/about" },
  ];

  return (
    <Navbar 
      onMenuOpenChange={setIsMenuOpen}
      maxWidth="full"
    >
      <div className="hidden max-sm:flex">
        <NavbarMenuToggle aria-label={isMenuOpen ? "Close menu" : "Open menu"} />
      </div>

      <NavbarBrand>
        <p className="font-bold text-inherit">JNU——Model Test Web</p>
      </NavbarBrand>

      <NavbarContent className="hidden sm:flex gap-4" justify="end">
        <NavbarItem>
          <Button as={Link} color="primary" href="/" variant="flat">
            Home Page
          </Button>
        </NavbarItem>
        <NavbarItem>
          <Button as={Link} color="primary" href="/about" variant="flat">
            About Us
          </Button>
        </NavbarItem>
      </NavbarContent>

      <NavbarMenu>
        {menuItems.map((item, index) => (
          <NavbarItem key={index}>
            <Link
              href={item.href}
              size="lg"
              color="primary"
              className="w-full"
            >
              {item.name}
            </Link>
          </NavbarItem>
        ))}
      </NavbarMenu>
    </Navbar>
  );
}
