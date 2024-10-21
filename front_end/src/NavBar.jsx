import {Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button} from "@nextui-org/react";

export default function NavBar() {
  return (
    <Navbar>
      <NavbarBrand>
        <p className="font-bold text-inherit">JNU——Model Test Web</p>
      </NavbarBrand>
      <NavbarContent className="hidden sm:flex gap-4" justify="center">
      </NavbarContent>
      <NavbarContent justify="end">
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
    </Navbar>
  );
}


