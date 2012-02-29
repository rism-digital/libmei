/*
    Copyright (c) 2011 Andrew Hankinson, Alastair Porter, Jamie Klassen, Mahtab Ghamsari-Esfahani, Gregory Burlet
    
    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:
    
    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#ifndef FACSIMILE_H_
#define FACSIMILE_H_

#include "meielement.h"
#include "meinamespace.h"
#include "exceptions.h"
/* #include_block */

#include "meicommon.h"
#include "sharedmixins.h"


namespace mei {
/** \brief 
 */
class MEI_EXPORT Facsimile : public MeiElement {
    public:
        Facsimile();
        Facsimile(const Facsimile& other);
        virtual ~Facsimile();

/* include <facsimile> */

        CommonMixIn    m_Common;
        DeclaringMixIn    m_Declaring;

    private:
        REGISTER_DECLARATION(Facsimile);
};

/** \brief 
 */
class MEI_EXPORT Surface : public MeiElement {
    public:
        Surface();
        Surface(const Surface& other);
        virtual ~Surface();

/* include <surface> */

        CommonMixIn    m_Common;
        CoordinatedMixIn    m_Coordinated;
        DatapointingMixIn    m_Datapointing;
        DeclaringMixIn    m_Declaring;
        StartidMixIn    m_Startid;

    private:
        REGISTER_DECLARATION(Surface);
};

/** \brief 
 */
class MEI_EXPORT Zone : public MeiElement {
    public:
        Zone();
        Zone(const Zone& other);
        virtual ~Zone();

/* include <zone> */

        CommonMixIn    m_Common;
        CoordinatedMixIn    m_Coordinated;
        DatapointingMixIn    m_Datapointing;

    private:
        REGISTER_DECLARATION(Zone);
};
}
#endif  // FACSIMILE_H_
