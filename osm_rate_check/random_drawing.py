# %%
import random
import os
from datetime import datetime

# Input: Dictionary of names and their entries
entries = {
    "mmann1123": 4,
    "l-izzo": 16,
    "isamah": 18,
    "livmakesmaps": 2,
    "kengaroo5445": 9,
    "brikin": 2,
    "caitnahc": 1,
    "conordoremus": 5,
    "lucycrino": 2,
    "bmrushing": 12,
    "Amac239": 2,
    "o_paq": 1,
}
# set seed based on date that the raffle is run
today_as_integer = int(datetime.now().strftime("%Y%m%d"))

random.seed(today_as_integer)


# Function to draw raffle tickets
def draw_raffle(entries, num_tickets):
    # Create a pool of names based on their entries
    pool = []
    for name, tickets in entries.items():
        pool.extend([name] * tickets)

    # Randomly select winners
    winners = random.sample(pool, num_tickets)
    return winners


# Number of tickets to draw
num_tickets = 2

# Run the raffle
winners = draw_raffle(entries, num_tickets)

# Print the winners
print("Raffle Winners:")
for i, winner in enumerate(winners, start=1):
    print(f"{i}: {winner}")

# %%
