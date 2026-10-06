import LootLlama from '../components/LootLlama'

export default function About() {
  return (
    <div className="about">
      <h1 className="page-title">About Us</h1>
      <div className="about-grid">
        <div className="panel">
          <h2>Who we are</h2>
          <p>
            Campus Customs is a New Haven shop that runs Yale Bulldog Blue, the official home for licensed Yale
            merch. We think school spirit should feel good to wear. That's why we focus on comfortable, classic
            pieces that work just as well in class as at The Game.
          </p>
          <h2>What we carry</h2>
          <p>
            Our item shop is mostly hoodies, crewnecks, quarter-zips and tees. The full store also carries hats,
            bags, drinkware and gifts. We have gear for all 14 residential colleges, 20+ varsity sports, Yale's
            graduate and professional schools, specific class years and even the family cheering from the stands.
          </p>
          <h2>Come visit</h2>
          <p>
            You'll find our store at <strong>57 Broadway, New Haven, CT 06511</strong>, right by campus. Stop in and
            try on a hoodie, or ask our chat llama to help you find the right fit online.
          </p>
        </div>
        <div className="panel panel-art">
          <LootLlama />
          <p className="panel-caption">Our mascot's mascot. Every order is a little loot drop.</p>
        </div>
      </div>
    </div>
  )
}
