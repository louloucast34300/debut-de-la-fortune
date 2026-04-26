import Image from "next/image"

export default async function DashboardPage() {
  return (
    <main className="dashboard-page">
      <div className="bg-image">
        <Image
          src="/images/dashboard.webp"
          alt="image du début de la fortune"
          fill={true}
          style={{ objectFit: 'cover' }}
        />
        <div className="bg-overlay" />
      </div>


      <div className="dashboard-content">

      </div>
    </main>
  );
}
