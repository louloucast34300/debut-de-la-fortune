import { LogoutButton } from "@/app/features/auth/login/atomic/logout/logout";
import { get_user_action } from "./features/auth/register/register.server";

export default async function Home() {
  const user = await get_user_action()

  return (
    <main>
      <h1>Hello {user.data.pseudo}</h1>
        <h1>Déconnexion</h1>
        <LogoutButton />
    </main>
  );
}
