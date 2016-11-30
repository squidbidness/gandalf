#ifndef VECTOR_HPP_DA39A3EE
#define VECTOR_HPP_DA39A3EE

#include <algorithm>
#include <array>
#include <initializer_list>

namespace geo {

	template< typename T, size_t N >
	struct Vector : std::array<T, N> {

	};

	using VectorF3 = Vector<float, 3>;

}

#endif
