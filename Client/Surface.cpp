#include "Surface.h"

Surface::Surface()
{

}

SDL_Surface *Surface::LoadFromImage(const std::string& FileName)
{
    SDL_Surface *Temp = NULL;
    SDL_Surface *Return = NULL;

    if((Temp = IMG_Load(FileName.c_str())) == NULL)
    {
        printf("Unable to load: %s", FileName.c_str());
        return NULL;
    }

    Return = SDL_DisplayFormat(Temp);
    SDL_FreeSurface(Temp);

    return Return;
}

bool Surface::Draw(SDL_Surface* Dest, SDL_Surface* Src, int X, int Y)
{
    if (Dest == NULL || Src == NULL)
    {
        return false;
    }

    SDL_Rect DestR;

    DestR.x = X;
    DestR.y = Y;

    SDL_BlitSurface(Src, NULL, Dest, &DestR);
    SDL_FreeSurface(Dest);

    return true;
}

bool Surface::Draw(SDL_Surface* Dest, SDL_Surface* Src, int X, int Y, int X2, int Y2, int W, int H)
{
    if(Dest == NULL || Src == NULL)
    {
        return false;
    }

    SDL_Rect DestR;

    DestR.x = X;
    DestR.y = Y;

    SDL_Rect SrcR;

    SrcR.x = X2;
    SrcR.y = Y2;
    SrcR.w = W;
    SrcR.h = H;

    SDL_BlitSurface(Src, &SrcR, Dest, &DestR);

    return true;
}

bool Surface::SetTransparent(SDL_Surface* Dest, int R, int G, int B)
{
    if(Dest == NULL)
    {
        return false;
    }

    SDL_SetColorKey(Dest, SDL_SRCCOLORKEY | SDL_RLEACCEL, SDL_MapRGB(Dest->format, R, G, B));

    return true;
}