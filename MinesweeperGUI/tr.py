import random
import pygame
import os
from time import sleep

class Game:
    def __init__(self, size, prob):
        self.board = Board(size, prob)
        pygame.init()
        self.sizeScreen = 600, 600
        self.screen = pygame.display.set_mode(self.sizeScreen)
        self.pieceSize = (self.sizeScreen[0] / size[1], self.sizeScreen[1] / size[0]) 
        self.loadPictures()
        self.solver = Solver(self.board)

    def loadPictures(self):
        self.images = {}
        imagesDirectory = "images"
        for fileName in os.listdir(imagesDirectory):
            if not fileName.endswith(".png"):
                continue
            path = imagesDirectory + r"/" + fileName 
            img = pygame.image.load(path)
            img = img.convert()
            img = pygame.transform.scale(img, (int(self.pieceSize[0]), int(self.pieceSize[1])))
            self.images[fileName.split(".")[0]] = img
            
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not (self.board.getWon() or self.board.getLost()):
                    rightClick = pygame.mouse.get_pressed(num_buttons=3)[2]
                    self.handleClick(pygame.mouse.get_pos(), rightClick)
                if event.type == pygame.KEYDOWN:
                    self.solver.move()
            self.screen.fill((0, 0, 0))
            self.draw()
            pygame.display.flip()
            if self.board.getWon():
                self.win()
                running = False
        pygame.quit()
        
    def draw(self):
        topLeft = (0, 0)
        for row in self.board.getBoard():
            for piece in row:
                rect = pygame.Rect(topLeft, self.pieceSize)
                image = self.images[self.getImageString(piece)]
                self.screen.blit(image, topLeft) 
                topLeft = topLeft[0] + self.pieceSize[0], topLeft[1]
            topLeft = (0, topLeft[1] + self.pieceSize[1])

    def getImageString(self, piece):
        if piece.getClicked():
            return str(piece.getNumAround()) if not piece.getHasBomb() else 'bomb-at-clicked-block'
        if (self.board.getLost()):
            if (piece.getHasBomb()):
                return 'unclicked-bomb'
            return 'wrong-flag' if piece.getFlagged() else 'empty-block'
        return 'flag' if piece.getFlagged() else 'empty-block'

    def handleClick(self, position, flag):
        index = tuple(int(pos // size) for pos, size in zip(position, self.pieceSize))[::-1] 
        self.board.handleClick(self.board.getPiece(index), flag)

    def win(self):
        sound = pygame.mixer.Sound('win.wav')
        sound.play()
        sleep(3)

class Board:
    def __init__(self, size, prob):
        self.size = size
        self.board = []
        self.won = False 
        self.lost = False
        for row in range(size[0]):
            row = []
            for col in range(size[1]):
                bomb = random.random() < prob
                piece = Piece(bomb)
                row.append(piece)
            self.board.append(row)
        self.setNeighbors()
        self.setNumAround()

    def print(self):
        for row in self.board:
            for piece in row:
                print(piece, end=" ")
            print()

    def getBoard(self):
        return self.board

    def getSize(self):
        return self.size
    
    def getPiece(self, index):
        return self.board[index[0]][index[1]]

    def handleClick(self, piece, flag):
        if piece.getClicked() or (piece.getFlagged() and not flag):
            return
        if flag:
            piece.toggleFlag()
            return
        piece.handleClick()
        if piece.getNumAround() == 0:
            for neighbor in piece.getNeighbors():
                self.handleClick(neighbor, False)
        if piece.getHasBomb():
            self.lost = True
        else:
            self.won = self.checkWon()
    
    def checkWon(self):
        for row in self.board:
            for piece in row:
                if not piece.getHasBomb() and not piece.getClicked():
                    return False
        return True

    def getWon(self):
        return self.won

    def getLost(self):
        return self.lost

    def setNeighbors(self):
        for row in range(len(self.board)):
            for col in range(len(self.board[0])):
                piece = self.board[row][col]
                neighbors = []
                self.addToNeighborsList(neighbors, row, col)
                piece.setNeighbors(neighbors)
    
    def addToNeighborsList(self, neighbors, row, col):
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                if r == row and c == col:
                    continue
                if r < 0 or r >= self.size[0] or c < 0 or c >= self.size[1]:
                    continue
                neighbors.append(self.board[r][c])
    
    def setNumAround(self):
        for row in self.board:
            for piece in row:
                piece.setNumAround()
        
class Piece:
    # States: Not clicked, clicked, flagged
    def __init__(self, hasBomb):
        self.hasBomb = hasBomb
        self.around = 0
        self.clicked = False
        self.flagged = False
        self.neighbors = []

    def __str__(self):
        return str(self.hasBomb)

    def getNumAround(self):
        return self.around

    def getHasBomb(self):
        return self.hasBomb

    def getClicked(self):
        return self.clicked

    def getFlagged(self):
        return self.flagged

    def toggleFlag(self):
        self.flagged = not self.flagged

    def handleClick(self):
        self.clicked = True

    def setNumAround(self):
        num = 0
        for neighbor in self.neighbors:
            if neighbor.getHasBomb():
                num += 1
        self.around = num

    def setNeighbors(self, neighbors):
        self.neighbors = neighbors
        
    def getNeighbors(self):
        return self.neighbors
 
class Solver:
    def __init__(self, board):
        self.board = board

    def move(self):
        for row in self.board.getBoard():
            for piece in row:
                if not piece.getClicked():
                    continue
                around = piece.getNumAround()
                unknown = 0
                flagged = 0
                neighbors = piece.getNeighbors()
                for p in neighbors:
                    if not p.getClicked():
                        unknown += 1
                    if p.getFlagged():
                        flagged += 1
                if around == flagged:
                    self.openUnflagged(neighbors)
                if around == unknown:
                    self.flagAll(neighbors)

    def openUnflagged(self, neighbors):
        for piece in neighbors:
            if not piece.getFlagged():
                self.board.handleClick(piece, False)


    def flagAll(self, neighbors):
        for piece in neighbors:
            if not piece.getFlagged():
                self.board.handleClick(piece, True)
            
def main():
    size = (9,9)
    prob = 0.1
    g = Game(size, prob)
    g.run()

if __name__ == '__main__':
    main()