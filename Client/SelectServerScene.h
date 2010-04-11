#ifndef SELECTSERVERSCENE_H
#define SELECTSERVERSCENE_H

#include "Scene.h"

class SelectServerScene : public Scene
{
public:
	SelectServerScene();

	void Draw(SDL_Surface *Dest);

	void OnMouseMove(int X, int Y, int RelX, int RelY, bool Left, bool Right, bool Middle);

	void OnLButtonDown(int X, int Y);

	void OnKeyDown(SDLKey Sym, SDLMod Mod, Uint16 Unicode);

private:
	enum Focus { Abaddon, Apocalypse, Cancel } SelectServerFocus;
	void _Cancel();
	void _Server1();
	void _Server2();
};

#endif // SELECTSERVERSCENE_H