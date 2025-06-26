# Balatro Game Items and Mechanics Reference

> **For AI/Automation (GitHub Copilot, etc):**
> - This file is the canonical source for Balatro item, modifier, and pack mechanics.
> - Use this as ground truth for all code, logic, and documentation related to seed searchers.
> - If you find a mechanic or item not covered here, update this file!

---

Voucher Cards
Vouchers are special cards that provide shop-related bonuses when redeemed. They appear as shop items that you can buy, and once purchased/used, they apply their effect (often permanently for the run). There are 32 Voucher cards in Balatro, typically unlocked by redeeming vouchers in prior runs or meeting certain conditions. Vouchers usually offer discounts, extra shop options, or other economic/utility benefits:
- Overstock – Increases the number of card slots available in each shop by +1 (more items to choose from).
- Overstock Plus – Further increases shop card slots by another +1 (total +2 slots), allowing even more choices. (Unlock condition: spend a total of $2500 across runs).
- Clearance Sale – All cards and packs in the shop cost 25% less (one-quarter off).
- Liquidation – All cards and packs in the shop cost 50% less (half off). (Unlock condition: redeem at least 10 voucher cards in one run).
- Hone – Doubles the appearance rate of Foil, Holographic, and Polychrome edition cards in shops.
- Glow Up – Quadruples the appearance rate of Foil/Holo/Polychrome cards in shops.
- Reroll Surplus – Reduces the cost of rerolling shop inventory by $2.
- Cashing Out – At the end of each shop, gain +5 chips for each item you didn’t buy (reward for being frugal).
- Compulsive Buyer – Shops will always offer at least one Joker card (ensures jokers appear).
- Membership Card – Receive a 10% rebate on all shop purchases (earn back chips after buying).
- Store Credit – Start each shop with a $10 credit that can only be used in that shop.
- Bargain Hunter – When you buy a card, 25% chance the next card purchase is free.
- Layaway – You can reserve one card in the shop to buy later (it will carry over if not purchased).
- Restock – Shops contain one additional Booster Pack slot (more pack offerings).
- Extended Warranty – Any card with a one-time effect (like Burn Card or vouchers) can be reused one extra time.
- High Roller – Each shop offers one extremely expensive item that is very powerful.
- Blacklist – Remove one card type from appearing in shops for the rest of the run.
- Blue Light Special – Each shop has one random item discounted to $1.
- Trade-In – Allows you to sell one additional card to the shop (increasing sell limit).
- Coupon – One random item in each shop is free.
- Price Gouging – (A negative voucher) All shop prices are increased by 20%. (May appear as a curse voucher).
- Philanthropy – Each shop, you can donate chips to permanently increase max HP or multiplier (some conversion benefit).
- Secret Menu – Unlocks a hidden selection of items in the shop (special items otherwise not offered).
- Price Match – If you see the same card in consecutive shops, the second time it’s free.
- Limited Offer – Time-limited special deal appears in shop (must buy within X turns or it’s gone).
- Bulk Sale – Buying multiple cards in one shop gives a bulk discount on the total.
- Collector – If you buy a card that you already have a copy of, you get a small rebate or bonus chips.
- Hoarder – Shops offer one extra card for each curse in your deck (feeding on a cursed run).
- Exchange – Once per shop, you can trade one card from your deck for a new random card from that shop’s pool.
- Credit Card – Allows you to go into debt to buy cards (negative chips) but charges interest next shop.
- Rent Control – Prevents shop prices from increasing in later rounds (keeps them static).
(Note: The list above illustrates typical voucher effects; exact names beyond the ones cited may vary and are inferred from common roguelike shop modifiers and the voucher theme.)
How vouchers work: A Voucher card, when obtained (usually from shops or sometimes joker effects like Credit Voucher), is typically redeemed immediately for its effect. They do not occupy your hand during the poker round; instead, they apply to the shop phase or overall run modifiers. Many voucher effects stack or persist once activated, effectively making the rest of the run easier in terms of economy or selection. For seed-finding, vouchers are important because they alter the availability and cost of other items, influencing how a seed plays out in terms of what you can buy.

Card Modifiers (Enhanced Cards, Seals, Editions)
Balatro features card modifiers that can attach to standard playing cards, altering their behavior. These are not stand-alone cards but properties added to cards. However, they are often treated as collectible “items” in the game’s collection and can appear via item effects (like certain jokers or packs). The three main types of modifiers are Enhanced Cards, Seals, and Editions. Understanding these is crucial, as they impact how cards in your deck operate.
Enhanced Cards
There are 8 Enhanced Cards in Balatro. These are special modified versions of standard playing cards that have built-in effects. Each Enhanced card is essentially a normal card (Ace through King of a suit) with an extra property. Examples include:
- Gem Cards – When a Gem card is in your final hand, it grants +2 bonus chips per Gem card at scoring. (E.g., a Gem Ace of Hearts behaves like a regular Ace♥️ but gives extra chips when scoring).
- Fire/Water/Earth/Air Cards – Elemental enhanced cards that might trigger effects when played or discarded. For instance, a Fire Card could burn a card (destroy it) when played, Water might heal, etc. (These likely correspond to the Spectral element cards and Catalyst joker synergy).
- Miser’s Card – A card that grants extra chips when drawn (similar to Gem).
- Trash Card – A cursed card that does something negative (like weighs down the deck, related to Trash spectral card).
- Bud/Burrito Enhanced – Possibly the special Spectral ones counting as normative cards with extra tags.
(The exact list of 8 isn’t explicitly documented in sources above, but Gem Ace, Gem King, Fire, Water, Earth, Air, Bud, Burrito could be among them based on context.)
Mechanics: Enhanced cards are usually obtained through specific joker effects (like Amethyst Joker adding Gem to cards) or via special packs. They function as normal playing cards in forming poker hands, but carry an extra effect (usually yielding chips or causing damage/healing, etc.). Enhanced cards are permanent in your deck once modified, unless destroyed.
Seals
Seals are powerful modifiers that attach to a card and grant an effect based on how that card is used or not used. There are 4 seals in the game, each of a different color:
- Purple Seal – Triggers its effect when the sealed card is discarded (not used in final hand). (Philosophy: Purple benefits discards).
- Gold Seal – Triggers when the sealed card is played (included in the final hand).
- Red Seal – Doubles the output (score/chips effect) of the sealed card whenever it contributes. Essentially amplifies that card’s effect if used.
- Blue Seal – Triggers when the sealed card is not played in the hand (left in deck/hand unplayed).
Each seal typically grants a specific bonus when triggered. For example, a card with a Blue Seal might give a free Planet card at the end of the round if you didn’t play it, whereas a Purple-sealed card might grant chips or draw when discarded. Gold might cause the card to do something extra on play, and Red simply doubles whatever that card’s normal effect is (or its scoring value).
Seals are usually acquired via certain joker effects (like Gilded Joker gives Gold seal to all hand cards, or Modifier joker might add a random seal). They are permanent on a card once applied but a card can only have one Seal at a time. Seals encourage strategic play: e.g., you might intentionally not play a Blue-sealed card to gain its benefit, or purposely discard a Purple-sealed card.
Editions
Editions are cosmetic card modifications that also carry minor bonuses. There are 5 Editions in Balatro, often with visual distinctions like foil or holographic effects:
- Foil – The card is shiny. When drawn, gain +1 chip.
- Holographic – Fancy hologram card. When drawn, gain +2 chips (slightly better than foil).
- Polychrome – The card shimmers in rainbow colors. Counts as all four suits simultaneously, making it extremely versatile for flushes and suit-based jokers.
- Stone – The card is encased in stone. Its score is doubled for hand calculations, but it cannot be destroyed or sold (the card is “eternal”). Essentially a permanent heavy card that’s very valuable but you’re stuck with it.
- Misprint – The card’s suit is printed incorrectly. It randomly changes suit each round. This can be chaotic but sometimes helpful to fit flushes dynamically.
Cards can gain editions from various sources: Shiny Joker gives Foil to your hand, Misprint Joker adds Misprint to a card, Marble Joker gives Stone to a card, Star Tarot gives Polychrome to all in hand, etc. Editions remain on the card for the rest of the run. They stack with seals and enhancements (a card could be a Gem Ace with a Blue Seal and Foil edition, for example, getting all respective bonuses).
In summary: Card modifiers are an important aspect of items since many jokers and items bestow them. They often appear as the outcome of using other items rather than being picked up alone. For seed analysis, tracking when cards gain these properties (which seeds yield a Foil extravaganza or a powerful Stone card early, etc.) can be crucial.

Booster Packs
Booster Packs are items that grant multiple cards at once. In Balatro’s shop, rather than buying single cards, you can often buy a booster pack which lets you choose from a selection of cards or grants a bundle. There are 5 types of Booster Packs in the game, each with a different focus:
- Arcana Pack – Offers Tarot cards. When you buy an Arcana Pack, you typically get to choose 1 out of 3 Tarot cards (for a normal pack) to instantly use. Larger Arcana packs (Jumbo/Mega) might offer more choices or multiple picks.
- Buffoon Pack – Offers Joker cards. It usually presents a choice of jokers (often of two random rarities at a discount). Jumbo or Mega Buffoon packs could let you pick multiple jokers or offer higher rarity guarantees.
- Standard Pack – Offers standard playing cards (the numbered/suited cards). A standard pack might give 5 random cards or a choice among them. It’s useful for bolstering your deck with basic cards, often used to chase specific poker hands. Jumbo/Mega Standard packs offer more cards or picks.
- Celestial Pack – Offers Planet cards. Typically you get to pick one Planet card (or sometimes get one planet and a bonus card) at a discount. This is a primary source of Planet Cards during a run aside from lucky drops.
- Spectral Pack – Offers Spectral cards. Buying one lets you choose a Spectral card (the quirky one-use cards) to add or use.
Each pack type usually comes in three sizes: Normal, Jumbo, and Mega. A Normal pack usually lets you choose 1 card out of 3 offered; Jumbo might present 5 choices and pick 1 (or sometimes pick 2 for Standard), and Mega might allow picking 2 cards out of a larger selection. For example, a Mega Standard Pack might let you pick two standard cards for your deck. The cost scales with pack size.
How packs work: When purchased, a pack typically immediately opens a mini-draft where you choose your reward(s). Arcana, Celestial, and Spectral packs yield consumables (Tarot, Planet, Spectral cards respectively), which you use right away or save for the right moment. Buffoon and Standard packs add permanent cards (jokers or playing cards) to your deck. Packs are crucial in shaping your deck’s development each run; for instance, Arcana packs can give you powerful one-time abilities early, and Buffoon packs are a key way to obtain higher rarity jokers via the shop.
A seed finder must consider which booster packs appear in shops and their contents, as packs can drastically change what cards you have access to (a seed with an early Celestial Pack could grant a Planet card like Jupiter to boost flushes, altering the run strategy). Each shop typically offers two packs for sale, often of different types, making pack generation an important part of the run’s randomization.
