-- Blunders by Phase
SELECT phase, COUNT(*) AS blunder_count
FROM moves
WHERE error_type = 'Blunder'
GROUP BY phase;

-- Tactical Motif Frequency
SELECT motif_type, COUNT(*) AS frequency
FROM motifs
GROUP BY motif_type
ORDER BY frequency DESC;

-- Average Centipawn Loss
SELECT AVG(centipawn_loss)
FROM moves;

-- Errors by Time Control
SELECT g.time_control, COUNT(m.error_type)
FROM games g
JOIN moves m ON g.game_id = m.game_id
WHERE m.error_type IN ('Blunder','Mistake','Inaccuracy')
GROUP BY g.time_control;