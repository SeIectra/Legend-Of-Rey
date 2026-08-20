def wall_collision(enemy, x_delta, y_delta, walls):
    new_x, new_y = enemy.x+x_delta, enemy.y+y_delta
    if not enemy.collides(new_x, new_y, walls):
        enemy.x, enemy.y = enemy.x + x_delta, enemy.y + y_delta
        return False
    else:
        enemy.x, enemy.y = enemy.x - x_delta, enemy.y - y_delta
        return True