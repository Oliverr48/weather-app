from midiutil import MIDIFile

# Create a MIDI file with one track
midi = MIDIFile(1)
track = 0
start_time = 0
midi.addTrackName(track, start_time, "Flume Style Melody")
midi.addTempo(track, start_time, 128)  # 128 BPM, common for EDM

# Define a more expressive, syncopated melody in a minor-ish feel (using notes from the C minor scale)
# This 2-bar phrase (8 beats total) contains 19 notes with varying durations.
# Notes: (pitch, duration in beats)
melody = [
    (60, 0.5),   # C4 for 0.5 beat
    (63, 0.25),  # Eb4 for 0.25 beat
    (65, 0.75),  # F4 for 0.75 beat
    (67, 0.5),   # G4 for 0.5 beat
    (68, 0.25),  # Ab4 for 0.25 beat
    (70, 0.25),  # Bb4 for 0.25 beat
    (72, 0.5),   # C5 for 0.5 beat
    (70, 0.5),   # Bb4 for 0.5 beat
    (68, 0.25),  # Ab4 for 0.25 beat
    (67, 0.25),  # G4 for 0.25 beat
    (65, 0.5),   # F4 for 0.5 beat
    (63, 0.5),   # Eb4 for 0.5 beat
    (60, 1.0),   # C4 for 1 beat (adds a breath)
    (63, 0.25),  # Eb4 for 0.25 beat
    (65, 0.25),  # F4 for 0.25 beat
    (67, 0.5),   # G4 for 0.5 beat
    (68, 0.25),  # Ab4 for 0.25 beat
    (70, 0.25),  # Bb4 for 0.25 beat
    (72, 0.5)    # C5 for 0.5 beat to finish the phrase
]

channel = 0
current_time = 0  # cumulative time tracker

# Add each note to the track with varied durations
for note, duration in melody:
    midi.addNote(track, channel, note, current_time, duration, 100)
    current_time += duration

# Save the MIDI file directly to your Desktop (Windows path provided)
file_path = "C:\\Users\\olive\\Desktop\\flume_style_melody.mid"

with open(file_path, "wb") as output_file:
    midi.writeFile(output_file)

print(f"MIDI file saved to: {file_path}")
